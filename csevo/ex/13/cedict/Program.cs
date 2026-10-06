// 슬라이드 p13-v12-ce-dict — 사전은 아직, C# 12
using System;
#if FZ
using System.Collections.Frozen;
#endif
using System.Collections.Generic;
using System.Collections.Immutable;

class Program
{
    static void Main()
    {
        var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };
        Dictionary<string, int> empty = [];   // no elements: fine
        Console.WriteLine(d.Count + " " + empty.Count);
#if BAD
        Dictionary<string, int> bad = [new("a", 1)];
#endif
        // .NET 10 builders take KeyValuePair elements
        ImmutableDictionary<string, int> im = [new("a", 1),
                                               new("a", 2)];
        Console.WriteLine(im.Count + " " + im["a"]);
#if FZ
        FrozenDictionary<string, int> fz = [new("x", 9)];
#endif
    }
}
