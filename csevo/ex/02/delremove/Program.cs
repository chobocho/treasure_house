// 슬라이드 p2-v1-delremove — -= 는 마지막으로 나온 것부터, C# 1.0
using System;

delegate void Act();

class App
{
    static void A() { Console.Write("A"); }
    static void B() { Console.Write("B"); }
    static void C() { Console.Write("C"); }

    static void Run(string label, Act d)
    {
        Console.Write(label + ": ");
        if (d == null) Console.Write("(null)"); else d();
        Console.WriteLine();
    }

    static void Main()
    {
        Act a = new Act(A), b = new Act(B), c = new Act(C);
        Act abab = (Act)Delegate.Combine(new Delegate[] { a, b, a, b });
        Run("abab      ", abab);
        Run("abab - a  ", abab - a);           // last A goes
        Run("abab - ab ", abab - (a + b));     // last "AB" run goes
        Run("abab - ba ", abab - (b + a));
        Run("abab - c  ", abab - c);           // absent: unchanged
        Run("abab - aa ", abab - (a + a));     // not a run: unchanged
        Run("a - a     ", a - a);              // empty list is null
        Act fresh = new Act(A);                // equal by method+target
        Console.WriteLine("fresh == a: " + (fresh == a));
        Run("abab - new A", abab - fresh);
    }
}
