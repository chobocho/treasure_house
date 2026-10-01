// 슬라이드 p2-v1-isas — is·as·캐스트, C# 1.0
using System;
using System.Collections;

class App
{
    static void Main()
    {
        object o = "text";
        object n = 42;
        object nothing = null;

        Console.WriteLine(o is string);           // True
        Console.WriteLine(n is string);           // False
        Console.WriteLine(nothing is string);     // False: null
        Console.WriteLine(n is IComparable);      // boxed int

        string s = o as string;                   // test + cast once
        string t = n as string;                   // null, no throw
        Console.WriteLine(s.Length + " " + (t == null));

        if (n is int)
        {
            int i = (int)n;                       // test, then cast
            Console.WriteLine(i + 1);
        }
        ICollection c = new ArrayList() as ICollection;
        Console.WriteLine(c.Count);
        string bad = (string)n;                   // cast throws
    }
}
