// 슬라이드 p13-v12-ce-range — .. 은 언제나 펼침, C# 12
using System;

class Program
{
    static void Main()
    {
        int[] xs = [1, 2, 3];
        int[] spread = [.. xs];             // spread element
        Range[] ranges = [(..2), 1..3, (..)]; // three ranges
        Console.WriteLine(spread.Length + " " + ranges.Length);
        foreach (Range r in ranges)
            Console.Write(r + " ");
        Console.WriteLine();
        bool b = true;
        int[] ys = [.. b ? xs : [9]];       // .. (b ? xs : [9])
        Console.WriteLine(string.Join(",", ys));
#if BAD
        Range[] bad = [..2];
#endif
    }
}
