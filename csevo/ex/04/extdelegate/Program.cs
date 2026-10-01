// 슬라이드 p4-v3-ext-delegate — 수신자가 Target 이 된다, C# 3.0
using System;

static class StringExt
{
    public static int WordCount(this string s)
    {
        return s.Split(' ').Length;
    }
}

class App
{
    static void Main()
    {
        string line = "to be or not";
        Func<int> count = line.WordCount;       // receiver is bound
        Console.WriteLine(count());
        Console.WriteLine("Target: " + count.Target);
        Console.WriteLine("Method: " + count.Method.DeclaringType.Name
            + "." + count.Method.Name);
    }
}
