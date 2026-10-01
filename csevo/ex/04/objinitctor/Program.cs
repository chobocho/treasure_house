// 슬라이드 p4-v3-objinit-ctor — 생성자 인자와 초기화자를 함께, C# 3.0
using System;

class Window
{
    public string Title;
    public int Width = 640;
    public int Height = 480;
    public Window(string title)
    {
        Title = title;
        Console.WriteLine("ctor: " + Width + "x" + Height);
    }
}

class Box
{
    public int Size;
}

class App
{
    static void Main()
    {
        Window w = new Window("main") { Width = 800 };
        Console.WriteLine(w.Title + " " + w.Width + "x" + w.Height);

        Box a = new Box() { Size = 1 };   // () is optional
        Box b = new Box { Size = 2 };
        Box c = new Box { };              // empty initializer
        Console.WriteLine(a.Size + b.Size + c.Size);
    }
}
