// 슬라이드 p9-v8-idx-init13 — 초기화자 안의 ^, C# 13
using System;

class Buffer
{
    public int[] Slots = new int[4];
    public int Length => Slots.Length;
    public int this[int i]
    {
        get => Slots[i];
        set => Slots[i] = value;
    }
}

class App
{
    static void Main()
    {
        // C# 13: an implicit Index indexer inside an object initializer
        var b = new Buffer { [0] = 1, [^1] = 9 };
        Console.WriteLine(string.Join(",", b.Slots));
    }
}
