// 슬라이드 p13-v12-cb-immutable — 불변 컬렉션도 [..] 로, C# 12
using System;
using System.Collections.Immutable;
using System.Linq;

class Program
{
    static void Main()
    {
        ImmutableArray<int> ia = [1, 2, 3];
        ImmutableList<string> il = ["a", "b"];
        ImmutableHashSet<int> hs = [3, 1, 3];
        IImmutableList<int> ii = [7, 8];
        Console.WriteLine(ia.Length + " " + il.Count + " " + hs.Count
                          + " " + ii.GetType().Name);
        // the old way
        var old = ImmutableArray.Create(1, 2, 3);
        Console.WriteLine(old.SequenceEqual(ia));
        ImmutableArray<int> bigger = [.. ia, 4];
        Console.WriteLine(ia.Length + " -> " + bigger.Length);
    }
}
