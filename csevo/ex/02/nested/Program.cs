// 슬라이드 p2-v1-nested — 중첩 형식, C# 1.0
using System;
using System.Reflection;

class Outer
{
    private static int secret = 7;

    public class Inner
    {
        public int Peek() { return secret; }    // sees private members
    }

    class Hidden { }                    // nested: private by default
    protected class Family { }

    public static Type HiddenType() { return typeof(Hidden); }
}

class App
{
    static void Main()
    {
        Outer.Inner i = new Outer.Inner();
        Console.WriteLine("Peek() = " + i.Peek());
        Console.WriteLine(typeof(Outer.Inner).FullName);
        Type h = Outer.HiddenType();
        Console.WriteLine(h.FullName + " private=" + h.IsNestedPrivate);
        Type f = typeof(Outer).GetNestedType("Family",
            BindingFlags.NonPublic);
        Console.WriteLine(f.FullName + " family=" + f.IsNestedFamily);
    }
}
