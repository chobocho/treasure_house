// 슬라이드 p5-v4-dyn-event — dynamic 의 += — 이벤트냐 덧셈이냐, C# 4.0
using System;

class Button
{
    public event EventHandler Click;
    public int Count = 0;

    public void Press()
    {
        if (Click != null) Click(this, EventArgs.Empty);
    }
}

class Program
{
    static void Main()
    {
        dynamic b = new Button();
        EventHandler h = delegate { Console.WriteLine("clicked"); };
        b.Click += h;          // run time: an event -> add accessor
        b.Count += 1;          // run time: a field -> get, add, set
        b.Press();
        b.Click -= h;
        b.Press();
        Console.WriteLine(b.Count);
    }
}
