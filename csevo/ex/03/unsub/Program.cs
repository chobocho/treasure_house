// 슬라이드 p3-v2-anon-unsub — 익명 메서드로 -= 하면, C# 2.0
using System;

class Button
{
    public event EventHandler Click;
    public void Press()
    {
        if (Click != null) Click(this, EventArgs.Empty);
        else Console.WriteLine("(no handler)");
    }
}

class App
{
    static void Main()
    {
        Button b = new Button();
        b.Click += delegate { Console.WriteLine("clicked"); };
        b.Click -= delegate { Console.WriteLine("clicked"); };
        b.Press();                            // still there

        Button c = new Button();
        EventHandler h = delegate { Console.WriteLine("clicked c"); };
        c.Click += h;
        c.Press();
        c.Click -= h;                         // keep it to remove it
        c.Press();
    }
}
