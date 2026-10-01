// 슬라이드 p3-v2-nullable-default — nullable 의 기본값은 null, C# 2.0
using System;

class Row
{
    public int? Score;                    // field: starts as null
}

class App
{
    static void Main()
    {
        Row r = new Row();
        Console.WriteLine(r.Score.HasValue);
        r.Score = 0;
        Console.WriteLine(r.Score.HasValue);
        Console.WriteLine(default(int?).HasValue);
        Console.WriteLine(new int?().HasValue);
        int?[] arr = new int?[2];
        Console.WriteLine(arr[0] == null);
    }
}
