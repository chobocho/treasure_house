// 슬라이드 p8-v7_2-span-slice — 자르기는 복사가 아니다, C# 7.2
using System;

class App
{
    static void Main()
    {
        string date = "2017-11-15";
        ReadOnlySpan<char> s = date.AsSpan();
        int y = int.Parse(s.Slice(0, 4));      // no Substring
        int m = int.Parse(s.Slice(5, 2));
        int d = int.Parse(s.Slice(8));
        Console.WriteLine(y + "/" + m + "/" + d);

        int[] arr = { 1, 2, 3, 4, 5 };
        Span<int> mid = arr.AsSpan(1, 3);       // a view, not a copy
        mid[0] = 20;
        mid.Slice(1).Fill(0);
        Console.WriteLine(string.Join(",", arr));
    }
}
