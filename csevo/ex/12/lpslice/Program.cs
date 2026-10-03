// 슬라이드 p12-v11-lp-slice — 슬라이스 패턴 .. var, C# 11
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        int[] arr = { 1, 2, 3, 4 };
        if (arr is [var first, .. var rest])
            Console.WriteLine("array : {0} | {1} : {2}", first,
                string.Join(",", rest), rest.GetType().Name);

        string s = "<hello>";
        if (s is ['<', .. var body, '>'])
            Console.WriteLine("string: {0} : {1}", body,
                body.GetType().Name);

        var list = new List<int> { 10, 20, 30 };
        if (list is [.. var init, var last])
            Console.WriteLine("list  : {0} | {1} : {2}",
                string.Join(",", init), last, init.GetType().Name);

        Span<int> span = arr;
        if (span is [_, .. var mid, _])
            Console.WriteLine("span  : {0} (Length {1})",
                string.Join(",", mid.ToArray()), mid.Length);

        if (arr is [.., var a, var b])
            Console.WriteLine("last two: {0} {1}", a, b);
    }
}
