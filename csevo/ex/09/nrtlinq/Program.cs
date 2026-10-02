// 슬라이드 p9-v8-nrt-linq — Where 는 형식을 좁히지 않는다, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;

class App
{
    static void Main()
    {
        var words = new List<string?> { "one", null, "three" };

        IEnumerable<int> a = words
            .Where(w => w != null)
            .Select(w => w.Length);            // CS8602

        IEnumerable<int> b = words
            .OfType<string>()                  // IEnumerable<string>
            .Select(w => w.Length);

        IEnumerable<int> c = words
            .Where(w => w != null)
            .Select(w => w!.Length);           // we know better

        Console.WriteLine(string.Join(",", a) + " " +
            string.Join(",", b) + " " + string.Join(",", c));
    }
}
