// 슬라이드 p4-v3-lambda-event — 이벤트 처리기를 람다로, C# 3.0
using System;

class Button
{
    public event EventHandler Click;
    public void PerformClick()
    {
        if (Click != null) Click(this, EventArgs.Empty);
    }
}

class App
{
    static void Main()
    {
        Button b = new Button();
        int clicks = 0;
        b.Click += (sender, e) => clicks++; // object, EventArgs
        b.Click += (sender, e) =>
            Console.WriteLine(sender.GetType().Name + " "
                + e.GetType().Name);
        b.PerformClick();
        b.PerformClick();
        Console.WriteLine("clicks = " + clicks);
    }
}
