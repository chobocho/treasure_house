// 슬라이드 p7-v6-eb-nullc — void 식 본문과 ?.Invoke, C# 6.0
using System;

class Button
{
    public event EventHandler Click;

    // a null-conditional call can be the whole body of a void method
    public void Fire() => Click?.Invoke(this, EventArgs.Empty);
}

class Program
{
    static void Main()
    {
        Button b = new Button();
        b.Fire();                                   // no handler yet
        b.Click += (s, e) => Console.WriteLine("clicked");
        b.Fire();
    }
}
