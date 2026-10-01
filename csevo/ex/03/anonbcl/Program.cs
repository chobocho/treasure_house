// 슬라이드 p3-v2-anon-bcl — List<T> 의 대리자 받는 메서드, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<int> xs = new List<int>(new int[] { 5, 2, 8, 1, 9 });
        int limit = 4;

        List<int> big =
            xs.FindAll(delegate(int x) { return x > limit; });
        List<string> s = xs.ConvertAll<string>(
            delegate(int x) { return "<" + x + ">"; });
        bool any = xs.Exists(delegate(int x) { return x > 8; });
        bool all = xs.TrueForAll(delegate(int x) { return x > 0; });
        int at = xs.FindIndex(delegate(int x) { return x == 8; });

        Console.WriteLine(big.Count + " " + any + " " + all + " " + at);
        s.ForEach(delegate(string t) { Console.Write(t); });
        Console.WriteLine();

        int removed =
            xs.RemoveAll(delegate(int x) { return x < limit; });
        xs.Sort(delegate(int a, int b) { return b.CompareTo(a); });
        Console.WriteLine(removed + ": " + string.Join(",",
            xs.ConvertAll<string>(delegate(int x)
                { return x.ToString(); }).ToArray()));
    }
}
