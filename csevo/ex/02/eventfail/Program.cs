// 슬라이드 p2-v1-eventfail — 밖에서는 += 와 -= 뿐, C# 1.0
using System;

delegate void Tick();

class Timer
{
    public event Tick Ticked;
    public void Fire() { if (Ticked != null) Ticked(); }
}

class App
{
    static void Beep() { }

    static void Main()
    {
        Timer t = new Timer();
        t.Ticked += new Tick(Beep);      // allowed
        t.Ticked = new Tick(Beep);       // replace everyone
        t.Ticked = null;                 // clear everyone
        t.Ticked();                      // raise from outside
        Tick copy = t.Ticked;            // read the list
    }
}
