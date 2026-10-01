// 슬라이드 p3-v2-variance-events — 처리기 하나로 여러 이벤트, C# 2.0
using System;

class KeyArgs : EventArgs { public char Key = 'k'; }
class MouseArgs : EventArgs { public int X = 7; }

delegate void KeyHandler(object sender, KeyArgs e);
delegate void MouseHandler(object sender, MouseArgs e);

class Window
{
    public event KeyHandler KeyDown;
    public event MouseHandler MouseMove;
    public void Simulate()
    {
        KeyDown(this, new KeyArgs());
        MouseMove(this, new MouseArgs());
    }
}

class App
{
    static void LogAny(object sender, EventArgs e)   // takes the base
    {
        Console.WriteLine("log " + e.GetType().Name);
    }

    static void Main()
    {
        Window w = new Window();
        w.KeyDown += LogAny;             // KeyArgs -> EventArgs
        w.MouseMove += LogAny;           // MouseArgs -> EventArgs
        w.Simulate();
    }
}
