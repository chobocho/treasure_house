// 슬라이드 p2-v1-eventfield — event 가 없으면 생기는 일, C# 1.0
using System;

delegate void Tick();

class Timer
{
    public Tick Ticked;              // a plain public delegate field
    public void Fire() { if (Ticked != null) Ticked(); }
}

class App
{
    static void Logger() { Console.WriteLine("  logger"); }
    static void Saver() { Console.WriteLine("  saver"); }
    static void Intruder() { Console.WriteLine("  intruder"); }

    static void Main()
    {
        Timer t = new Timer();
        t.Ticked += new Tick(Logger);
        t.Ticked += new Tick(Saver);
        Console.WriteLine("fire:");
        t.Fire();

        t.Ticked = new Tick(Intruder);   // = instead of +=, compiles
        Console.WriteLine("fire again:");
        t.Fire();
        Console.WriteLine("raised from outside:");
        t.Ticked();
    }
}
