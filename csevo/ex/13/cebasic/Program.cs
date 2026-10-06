// 슬라이드 p13-v12-collexpr — 컬렉션 식, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        int[] a = [1, 2, 3];
        List<string> b = ["one", "two", "three"];
        Span<char> c = ['a', 'b', 'c'];
        int[][] twoD = [[1, 2], [3, 4, 5]];
        WriteBytes([1, 2, 3]);          // argument: byte[]

        Console.WriteLine(a.Length + " " + b[2] + " " + c.ToString());
        Console.WriteLine(twoD[1].Length);
    }

    static void WriteBytes(byte[] x)
    {
        Console.WriteLine(BitConverter.ToString(x));
    }
}
