// 슬라이드 p14-v13-ii-range — 초기화자 안의 범위 인덱서, C# 13
using System;

class Buf
{
    public int[] A = new int[8];
    public int Length => A.Length;
    public int[] Slice(int start, int length)
    {
        Console.WriteLine("  Slice(" + start + ", " + length + ")");
        return A;
    }
}

class Holder
{
    public Buf B { get; } = new Buf();
    public int[] Arr { get; } = new int[4];
}

class Program
{
    static void Main()
    {
        Console.WriteLine("initializer:");
        var h = new Holder
        {
            B = { [1..3] = { [0] = 5 }, [2..^1] = { [0] = 6 } }
        };
        Console.WriteLine("statement:");
        int[] s = h.B[1..3];
        s = h.B[2..^1];
        Console.WriteLine("array:");
        var g = new Holder { Arr = { [1..3] = { [0] = 7 } } };
        Console.WriteLine("  " + string.Join(" ", g.Arr));
    }
}
