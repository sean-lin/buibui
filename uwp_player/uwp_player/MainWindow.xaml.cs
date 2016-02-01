using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Diagnostics;

namespace uwp_player
{
    using LitJson;
    using System.IO;
    using System.Net;
    using System.Windows.Threading;
    using Position = Tuple<double, double>;

    public class DanmakuConfig {
        public const int DANMAKU_TTL = 10;
        public const int HORIZONTAL_PADDING = 20;
        public const int LAYER_OFFSET = 15;
        public const string DANMAKU_SERVER_URL = "http://172.16.100.117:8080/buibui/get_danmakus";
        public const int DANMAKU_SERVER_QUERY_INTERVAL = 1;
    };

    public enum DanmakuMode
    {
        Right2Left = 0,
        Left2Right = 1,
        Top = 2,
        Bottom = 3,
    };

    public class DanmakuLib
    {
        public static Tuple<bool, double> getSlotFromTop(Size danmakuSize, double offset, double screenHeight, List<Position> barrier)
        {
            barrier.Add(new Position(screenHeight, 0));
            barrier.Sort(positionCmp);

            var y = offset;
            foreach (var i in barrier)
            {
                if (i.Item1 > y && i.Item1 > danmakuSize.Height + y)
                {
                    return new Tuple<bool, double>(true, y);
                }
                y = i.Item1 + i.Item2 + 1;
            }
            return new Tuple<bool, double>(false, 0);
        }

        public static Tuple<bool, double> getSlotFromBottom(Size danmakuSize, double offset, double screenHeight, List<Position> barrier)
        {
            barrier.Add(new Position(0, 0));
            barrier.Sort(positionCmp);
            barrier.Reverse();

            var y = screenHeight - danmakuSize.Height - offset;
            Debug.Print(String.Format("Y: {0}/{1}  height: {2}", y, screenHeight, danmakuSize.Height));
            foreach (var i in barrier)
            {
                if (i.Item1 + i.Item2 < y && i.Item1 < y)
                {
                    return new Tuple<bool, double>(true, y);
                }
                y = i.Item1 - danmakuSize.Height - 1;
            }
            return new Tuple<bool, double>(false, 0);
        }

        public static void attachHorizontalTransform(TextBlock tb, EventHandler handler, Point pos, double start, double end, int ttl)
        {
            TranslateTransform trans = new TranslateTransform();
            AnimationTimeline ani = new DoubleAnimation(start, end, TimeSpan.FromSeconds(ttl));
            ani.Completed += handler;
            trans.X = pos.X;
            trans.Y = pos.Y;
            tb.RenderTransform = trans;

            trans.BeginAnimation(TranslateTransform.XProperty, ani);
        }

        public static void attachStaticTransform(TextBlock tb, EventHandler handler, Point pos, int ttl)
        {
            TranslateTransform trans = new TranslateTransform();
            trans.Y = pos.Y;
            trans.X = pos.X;
            tb.RenderTransform = trans;

            var timer = new DispatcherTimer() { Interval = TimeSpan.FromSeconds(ttl) };
            timer.Tick += (sender, args) => {
                handler(sender, args);
                timer.Stop();
            };
            timer.Start();
        }

        public static List<Position> getPosition(List<TextBlock> tbs)
        {
            var ret = new List<Position>();
            foreach (var i in tbs) {
                var y = ((TranslateTransform)i.RenderTransform).Y;
                ret.Add(new Position(y, i.ActualHeight));
            }
            return ret;
        }

        protected static int positionCmp(Position x, Position y)
        {
            if (x.Item1 > y.Item1)
            {
                return 1;
            }
            else if (x.Item1 < y.Item1)
            {
                return -1;
            }
            return 0;
        }
    }

    public interface IDanmakuAllocator
    {
        bool allocate(TextBlock tb);
        bool free(TextBlock tb);
    }

    public abstract class DanmakuLayerAllocator : IDanmakuAllocator
    {
        protected Canvas canvas;
        protected double offset;
        protected List<TextBlock> pool;

        public DanmakuLayerAllocator(Canvas canvas, double offset)
        {
            this.canvas = canvas;
            this.offset = offset;
            this.pool = new List<TextBlock>();
        }

        public virtual bool allocate(TextBlock tb)
        {
            var size = new Size(tb.ActualHeight, tb.ActualWidth);
            var ret = allocateY(size);
            if (ret.Item1) {
                attachTransform(tb, (s, a) =>
                {
                    free(tb);
                }, ret.Item2);
                canvas.Children.Add(tb);
                pool.Add(tb);
                return true;
            }
            return false;
        }
        public virtual bool free(TextBlock tb)
        {
            if (this.pool.Remove(tb))
            {
                canvas.Children.Remove(tb);
                return true;
            }
            return false;
        }

        protected abstract Tuple<bool, double> allocateY(Size size);

        protected abstract void attachTransform(TextBlock tb, EventHandler handler, double y);

    }

    public class DanmakuRight2LeftLayerAllocator: DanmakuLayerAllocator
    { 
        public DanmakuRight2LeftLayerAllocator(Canvas c, double offset): base(c, offset) { }

        protected override Tuple<bool, double> allocateY(Size size)
        {
            // 获取出可能阻挡新弹幕的旧弹幕
            var barrier = DanmakuLib.getPosition(pool.FindAll((i) =>
            {
                var x = ((TranslateTransform)i.RenderTransform).X;
                return i.ActualWidth + x + DanmakuConfig.HORIZONTAL_PADDING > canvas.Width;
            }));
            return DanmakuLib.getSlotFromTop(size, offset, canvas.Height, barrier);
        }
        protected override void attachTransform(TextBlock tb, EventHandler handler, double y)
        {
            DanmakuLib.attachHorizontalTransform(tb, handler,
                new Point(0, y), canvas.Width, -tb.ActualWidth, DanmakuConfig.DANMAKU_TTL);
        }
    };

    public class DanmakuLeft2RightLayerAllocator: DanmakuLayerAllocator
    {
        public DanmakuLeft2RightLayerAllocator(Canvas c, double offset): base(c, offset) { }

        protected override Tuple<bool, double> allocateY(Size size)
        {
            var barrier = DanmakuLib.getPosition(pool.FindAll((i) =>
            {
                var x = ((TranslateTransform)i.RenderTransform).X;
                return x - DanmakuConfig.HORIZONTAL_PADDING < 0;
            }));
            return DanmakuLib.getSlotFromTop(size, offset, canvas.Height, barrier);
        }
        protected override void attachTransform(TextBlock tb, EventHandler handler, double y)
        {
            DanmakuLib.attachHorizontalTransform(tb, handler,
                new Point(0, y), -tb.ActualWidth, canvas.Width, DanmakuConfig.DANMAKU_TTL);
        }
    }

    public class DanmakuTopLayerAllocator: DanmakuLayerAllocator
    {
        public DanmakuTopLayerAllocator(Canvas c, double offset) : base(c, offset) { }

        protected override Tuple<bool, double> allocateY(Size size)
        {
            var barrier = DanmakuLib.getPosition(pool);
            return DanmakuLib.getSlotFromTop(size, offset, canvas.Height, barrier);
        }
        protected override void attachTransform(TextBlock tb, EventHandler handler, double y)
        {
            var x = (canvas.Width - tb.ActualWidth) / 2;
            DanmakuLib.attachStaticTransform(tb, handler, new Point(x, y), DanmakuConfig.DANMAKU_TTL/2);
        }
    }

    public class DanmakuBottomLayerAllocator: DanmakuLayerAllocator
    {
        public DanmakuBottomLayerAllocator(Canvas c, double offset) : base(c, offset) { }

        protected override Tuple<bool, double> allocateY(Size size)
        {
            var barrier = DanmakuLib.getPosition(pool);
            return DanmakuLib.getSlotFromBottom(size, offset, canvas.Height, barrier);
        }
        protected override void attachTransform(TextBlock tb, EventHandler handler, double y)
        {
            var x = (canvas.Width - tb.ActualWidth) / 2;
            DanmakuLib.attachStaticTransform(tb, handler, new Point(x, y), DanmakuConfig.DANMAKU_TTL/2);
        }
    }

    public class DanmakuAllocator: IDanmakuAllocator
    {
        private List<IDanmakuAllocator> layers;
        DanmakuMode mode;
        Canvas canvas;
        
        public DanmakuAllocator(Canvas canvas, DanmakuMode mode)
        {
            this.canvas = canvas;
            this.mode = mode;
            layers = new List<IDanmakuAllocator>();
        }

        public bool allocate(TextBlock tb)
        {
            foreach(var i in layers)
            {
                if (i.allocate(tb))
                {
                    return true;
                }
            }
            var layer = newLayerAllocator(getOffset());
            this.layers.Add(layer);
            return layer.allocate(tb);
        }

        public bool free(TextBlock tb)
        {
            foreach(var i in layers)
            {
                if(i.free(tb))
                {
                    return true;
                }
            }
            return false;
        }

        private double getOffset()
        {
            return (layers.Count() * DanmakuConfig.LAYER_OFFSET) % canvas.Height;
        }

        private IDanmakuAllocator newLayerAllocator(double offset)
        {
            switch(mode)
            {
                case DanmakuMode.Left2Right:
                    return new DanmakuLeft2RightLayerAllocator(canvas, offset);
                case DanmakuMode.Right2Left:
                    return new DanmakuRight2LeftLayerAllocator(canvas, offset);
                case DanmakuMode.Top:
                    return new DanmakuTopLayerAllocator(canvas, offset);
                case DanmakuMode.Bottom:
                    return new DanmakuBottomLayerAllocator(canvas, offset);
            }
            return null;
        }
    }

    /// <summary>
    /// MainWindow.xaml 的交互逻辑
    /// </summary>
    public partial class MainWindow : Window
    {
        private Dictionary<DanmakuMode, IDanmakuAllocator> allocators;
        private WebClient wc;
        private long last_time;
        private Dictionary<int, double> font_map;

        public MainWindow()
        {
            InitializeComponent();
            DispatcherTimer dispatcherTimer = new DispatcherTimer();
            dispatcherTimer.Tick += on_update_timer;
            dispatcherTimer.Interval = new TimeSpan(0, 0, DanmakuConfig.DANMAKU_SERVER_QUERY_INTERVAL);
            dispatcherTimer.Start();
            mCanvas.Width = this.Width;
            mCanvas.Height = this.Height;

            allocators = new Dictionary<DanmakuMode, IDanmakuAllocator>();
            allocators.Add(DanmakuMode.Left2Right, new DanmakuAllocator(mCanvas, DanmakuMode.Left2Right));
            allocators.Add(DanmakuMode.Right2Left, new DanmakuAllocator(mCanvas, DanmakuMode.Right2Left));
            allocators.Add(DanmakuMode.Top, new DanmakuAllocator(mCanvas, DanmakuMode.Top));
            allocators.Add(DanmakuMode.Bottom, new DanmakuAllocator(mCanvas, DanmakuMode.Bottom));

            wc = new WebClient();
            wc.OpenReadCompleted += (o, a) =>
            {
                try
                {
                    var stream = new StreamReader(a.Result);
                    var data = JsonMapper.ToObject<HttpReq>(stream.ReadToEnd());
                    processServerResponse(data.danmakus);
                }
                catch (Exception)
                {
                    Debug.Print("rpc error");
                }
            };

            TimeSpan t = DateTime.UtcNow - new DateTime(1970, 1, 1);
            last_time = (long)t.TotalSeconds * 1000;

            font_map = new Dictionary<int, double>();
            font_map[1] = 0.03;
            font_map[2] = 0.06;
            font_map[3] = 0.1;
            font_map[4] = 0.15;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (e.Key == Key.Escape)
            {
                Close();
            }
        }

        private void addDanmaku(String str, Color color, double size, DanmakuMode mode)
        {
            var tb = new TextBlock()
            {
                Text = str,
                Foreground = new SolidColorBrush(color),
                FontSize = size,
                MinWidth = 0,
                MinHeight = 0,
                MaxWidth = double.PositiveInfinity,
                MaxHeight = double.PositiveInfinity,
            };
            tb.Measure(new Size(0, 0));
            tb.Arrange(new Rect());

            allocators[mode].allocate(tb);
        }

        private void on_update_timer(object sender, EventArgs e)
        {
            if (!wc.IsBusy)
            {
                var uri = new Uri(DanmakuConfig.DANMAKU_SERVER_URL + "?ts=" + last_time.ToString());
                wc.OpenReadAsync(uri);
            }
            if (mCanvas.Width != Width)
            {
                mCanvas.Width = Width;
            }
            if (mCanvas.Height != Height)
            {
                mCanvas.Height = Height;
            }
        }

        private void processServerResponse(List<DanmakuMessage> msgs)
        {
            msgs.Sort((x, y) =>
            {
                if (x.ts == y.ts) return 0;
                return (x.ts > y.ts)?1:-1;
            });
            if(msgs.Count > 0)
            {
                var ts = msgs.Last().ts;
                if(ts > last_time)
                {
                    last_time = ts;
                }
            }
            foreach(var i in msgs)
            {
                var clr = (Color)ColorConverter.ConvertFromString(i.color);
                var mode = (DanmakuMode)i.mode;
                var size = font_map[i.size] * mCanvas.Height;
                addDanmaku(i.text, clr, size, mode);
            }
        }

        private long now()
        {
            TimeSpan t = DateTime.UtcNow - new DateTime(1970, 1, 1);
            return (long)t.TotalSeconds * 1000;
        }
    }
    public struct DanmakuMessage
    {
        public string text;
        public int mode;
        public int size;
        public string color;
        public long ts;
    };

    public struct HttpReq
    {
        public List<DanmakuMessage> danmakus;
    }
}
