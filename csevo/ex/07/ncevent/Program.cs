// 슬라이드 p7-v6-nullcond-event — 이벤트 올리기, C# 6.0
using System;

class Door
{
    public event EventHandler Opened;

    public void OpenOld()                       // C# 5 idiom
    {
        EventHandler handler = Opened;          // copy first
        if (handler != null)
            handler(this, EventArgs.Empty);
    }

    public void OpenNew()                       // C# 6
    {
        Opened?.Invoke(this, EventArgs.Empty);
    }
}

class App
{
    static void Main()
    {
        var d = new Door();
        d.OpenOld();                            // no subscribers
        d.OpenNew();
        Console.WriteLine("no handler: nothing happened");
        d.Opened += (s, e) => Console.WriteLine("opened");
        d.OpenOld();
        d.OpenNew();
    }
}
