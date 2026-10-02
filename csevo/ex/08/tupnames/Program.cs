// 슬라이드 p8-v7-tuple-names — 이름은 컴파일 시간에만 있다, C# 7.0
using System;
using System.Linq;

class App
{
    static (int min, int max) Range() => (3, 9);

    static void Main()
    {
        var r = Range();
        Console.WriteLine(r.min + " " + r.max);     // names in source
        Console.WriteLine(r.Item1 + " " + r.Item2); // the real fields
        Console.WriteLine(r.ToString());            // no names
        Type t = r.GetType();
        Console.WriteLine(t.Name + ": " + string.Join(", ",
            t.GetFields().Select(f => f.Name)));
        Console.WriteLine(t.GetField("min") == null);
        (int lo, int hi) other = r;                  // same type
        Console.WriteLine(other.GetType() == t);
    }
}
