// 슬라이드 p9-v8-range-type — System.Range 라는 값, C# 8.0
using System;

class App
{
    static void Main()
    {
        Range r = 2..^1;
        Console.WriteLine("{0}  Start={1} End={2}", r, r.Start, r.End);
        // what the operator lowers to: constructor or factory
        Console.WriteLine(r.Equals(new Range(2, ^1)));
        Console.WriteLine(Range.All.Equals(..));
        Console.WriteLine(Range.StartAt(3).Equals(3..));
        Console.WriteLine(Range.EndAt(^2).Equals(..^2));

        // the same Range means different slices per length
        foreach (int len in new[] { 5, 10 })
        {
            var (off, n) = r.GetOffsetAndLength(len);
            Console.WriteLine("length {0,2}: offset {1}, count {2}",
                len, off, n);
        }
    }
}
