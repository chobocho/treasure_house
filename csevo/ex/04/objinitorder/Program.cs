// 슬라이드 p4-v3-objinit-order — 생성자 다음, 적은 차례대로, C# 3.0
using System;

class Probe
{
    int a, b;
    public Probe() { Console.WriteLine("ctor"); }
    public int A
    {
        get { return a; }
        set { Console.WriteLine("  set A = " + value); a = value; }
    }
    public int B
    {
        get { return b; }
        set { Console.WriteLine("  set B = " + value); b = value; }
    }
}

class App
{
    static int Eval(string what, int v)
    {
        Console.WriteLine("  eval " + what);
        return v;
    }

    static void Main()
    {
        Probe p = new Probe { B = Eval("B", 2), A = Eval("A", 1) };
        Console.WriteLine("p.A=" + p.A + " p.B=" + p.B);
    }
}
