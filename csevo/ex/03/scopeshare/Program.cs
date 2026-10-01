// 슬라이드 p3-v2-closure-scope-share — 한 스코프, 한 객체, C# 2.0
using System;
using System.Reflection;

delegate int D();

class App
{
    static D small;

    static void Setup()
    {
        int counter = 0;
        byte[] big = new byte[1000000];
        small = delegate { return ++counter; };   // uses counter only
        D once = delegate { return big.Length; }; // uses big
        Console.WriteLine("once: " + once());
        Console.WriteLine("same target: "
            + (small.Target == once.Target));
    }

    static void Main()
    {
        Setup();
        string[] names = new string[2];
        FieldInfo[] fs = small.Target.GetType().GetFields();
        for (int i = 0; i < fs.Length; i++)
            names[i] = fs[i].FieldType.Name;
        Array.Sort(names, StringComparer.Ordinal);
        Console.WriteLine("small keeps: " + string.Join(", ", names));
    }
}
