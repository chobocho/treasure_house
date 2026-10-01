// 슬라이드 p2-v1-using — using 문과 IDisposable, C# 1.0
using System;

class Res : IDisposable
{
    string name;
    public Res(string name) { this.name = name; Say("open"); }
    public void Use(bool fail)
    {
        Say("use");
        if (fail) throw new InvalidOperationException(name + " failed");
    }
    public void Dispose() { Say("dispose"); }
    void Say(string s) { Console.WriteLine("  " + name + ": " + s); }
}

class App
{
    static void Main()
    {
        Console.WriteLine("nested:");
        using (Res a = new Res("a"))
        using (Res b = new Res("b"))     // disposed in reverse order
        {
            a.Use(false);
            b.Use(false);
        }
        Console.WriteLine("with an exception:");
        try
        {
            using (Res c = new Res("c"))
                c.Use(true);
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine("  caught: " + e.Message);
        }
    }
}
