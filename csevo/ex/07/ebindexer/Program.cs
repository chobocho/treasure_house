// 슬라이드 p7-v6-exprbody-indexer — 식 본문 인덱서, C# 6.0
using System;

class Week
{
    string[] days = { "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" };

    // a get-only indexer written with =>
    public string this[int i] => days[i % 7];
}

class Program
{
    static void Main()
    {
        Week w = new Week();
        Console.WriteLine(w[0] + " " + w[6] + " " + w[9]);
    }
}
