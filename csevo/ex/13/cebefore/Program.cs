// 슬라이드 p13-v12-ce-why — 컬렉션 식 이전의 여섯 가지 꼴, C# 11
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        int[] x1 = new int[] { 1, 2, 3, 4 };
        int[] x2 = Array.Empty<int>();
        WriteBytes(new[] { (byte)1, (byte)2, (byte)3 });
        List<int> x4 = new() { 1, 2, 3, 4 };
        Span<int> s1 = stackalloc int[] { 5, 6 };
        Span<int> s2 = new int[] { 7, 8 };   // heap array as span
        Console.WriteLine(x1.Length + " " + x2.Length + " "
                          + x4.Count + " " + s1[1] + " " + s2[0]);
    }

    static void WriteBytes(byte[] b)
    {
        Console.WriteLine(BitConverter.ToString(b));
    }
}
