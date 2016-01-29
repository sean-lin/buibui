using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace uwp_player
{
    using LitJson;
    using System.Diagnostics;
    using System.IO;
    using System.Net;
    using System.Windows.Threading;    /// <summary>
                                       /// MainWindow.xaml 的交互逻辑
                                       /// </summary>

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

    public interface IDanmakuAllocator
    {
        bool allocate(TextBlock tb);
        bool free(TextBlock tb);
    }

    public class DanmakuLayerAllocator : IDanmakuAllocator
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
            var height = tb.DesiredSize.Height;

            var barrier = getBarrierPos();
            var y = offset;
            foreach(var i in barrier)
            {
                if(i.Item1 > y && i.Item1 > height + y)
                {
                    bindTranslateTransform(tb, y);
                    return true;
                }
                y = i.Item1 + i.Item2 + 1;
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


        // 获取出可能阻挡新弹幕的旧弹幕
        protected virtual List<Position> getBarrierPos()
        {
            var ret = new List<Position>();
            List<TextBlock> base_line = getBarrier();

            base_line.ForEach((i) =>
            {
                var y = ((TranslateTransform)i.RenderTransform).Y;
                ret.Add(new Position(y, i.DesiredSize.Height));
            });
            ret.Add(new Position(canvas.Height, 0));
            ret.Sort(positionCmp);
            return ret;
        }

        protected int positionCmp(Position x, Position y)
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

        protected virtual List<TextBlock> getBarrier()
        {
            return pool.FindAll((i) =>
            {
                var x = ((TranslateTransform)i.RenderTransform).X;
                return i.DesiredSize.Width + x + DanmakuConfig.HORIZONTAL_PADDING > canvas.Width;
            });
        }

        protected virtual void bindTranslateTransform(TextBlock tb, double y)
        {

            TranslateTransform trans = new TranslateTransform();
            AnimationTimeline ani = genAnimation();
            ani.Completed += (s, a) =>
            {
                free(tb);
            };
            trans.Y = y;
            trans.BeginAnimation(TranslateTransform.XProperty, ani);

            tb.RenderTransform = trans;

            canvas.Children.Add(tb);
            this.pool.Add(tb);

            trans.BeginAnimation(TranslateTransform.XProperty, ani);
        }

        protected virtual AnimationTimeline genAnimation()
        {
            return new DoubleAnimation(canvas.Width, 0, TimeSpan.FromSeconds(DanmakuConfig.DANMAKU_TTL));
        }
    };

    public class DanmakuLeft2RightLayerAllocator: DanmakuLayerAllocator
    {
        public DanmakuLeft2RightLayerAllocator(Canvas c, double offset): base(c, offset) { }

        protected override List<TextBlock> getBarrier()
        {
            return pool.FindAll((i) =>
            {
                var x = ((TranslateTransform)i.RenderTransform).X;
                return x - DanmakuConfig.HORIZONTAL_PADDING < 0;
            });
        }
        protected override AnimationTimeline genAnimation()
        {
            return new DoubleAnimation(0, canvas.Width, TimeSpan.FromSeconds(DanmakuConfig.DANMAKU_TTL));
        }
    }

    public class DanmakuTopLayerAllocator: DanmakuLayerAllocator
    {
        public DanmakuTopLayerAllocator(Canvas c, double offset) : base(c, offset) { }

        protected override List<TextBlock> getBarrier()
        {
            return pool;
        }

        protected override void bindTranslateTransform(TextBlock tb, double y)
        {

            TranslateTransform trans = new TranslateTransform();
            trans.Y = y;
            trans.X = (canvas.Width - tb.DesiredSize.Width) / 2;
            tb.RenderTransform = trans;

            canvas.Children.Add(tb);
            this.pool.Add(tb);

            var timer = new DispatcherTimer() { Interval = TimeSpan.FromSeconds(DanmakuConfig.DANMAKU_TTL)};
            timer.Tick += (sender, args) => {
                canvas.Children.Remove(tb);
                timer.Stop();
            };
            timer.Start();
        }
    }
    public class DanmakuBottomLayerAllocator: DanmakuTopLayerAllocator
    {
        public DanmakuBottomLayerAllocator(Canvas c, double offset) : base(c, offset) { }

        public override bool allocate(TextBlock tb)
        {
            var height = tb.DesiredSize.Height;

            var barrier = getBarrierPos();
            var y = canvas.Height - height - offset;
            foreach(var i in barrier)
            {
                if(i.Item1 + i.Item2 < y && i.Item1 < y)
                {
                    bindTranslateTransform(tb, y);
                    return true;
                }
                y = i.Item1 - height - 1;
            }
            return false;
        }
        protected override List<Position> getBarrierPos()
        {
            var ret = new List<Position>();
            List<TextBlock> base_line = getBarrier();

            base_line.ForEach((i) =>
            {
                var y = ((TranslateTransform)i.RenderTransform).Y;
                ret.Add(new Position(y, i.DesiredSize.Height));
            });
            ret.Add(new Position(0, 0));
            ret.Sort(positionCmp);
            ret.Reverse();
            return ret;
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
                    return new DanmakuLayerAllocator(canvas, offset);
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
            System.Windows.Threading.DispatcherTimer dispatcherTimer = new System.Windows.Threading.DispatcherTimer();
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
                var stream = new StreamReader(a.Result);
                var data = JsonMapper.ToObject<HttpReq>(stream.ReadToEnd());
                processServerResponse(data.danmakus);
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
                MaxWidth = double.PositiveInfinity,
            };
            tb.Measure(new Size());

            allocators[mode].allocate(tb);
        }

        private void on_update_timer(object sender, EventArgs e)
        {
            if (!wc.IsBusy)
            {
                var uri = new Uri(DanmakuConfig.DANMAKU_SERVER_URL + "?ts=" + last_time.ToString());
                wc.OpenReadAsync(uri);
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
