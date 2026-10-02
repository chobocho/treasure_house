// 슬라이드 p8-v7_3-exprvar — 초기화자와 쿼리의 식 변수, C# 7.3
using System;
using System.Linq;

class Config
{
    static readonly string Raw = "8080";
    // a field initializer may declare 'out var'
    public static readonly int Port =
        int.TryParse(Raw, out var p) ? p : 80;
    public bool IsText { get; } = Raw is string s && s.Length > 0;
}

class App
{
    static void Main()
    {
        Console.WriteLine(Config.Port + " " + new Config().IsText);
        var input = new[] { "1", "x", "30", "4" };
        var big = from t in input
                  where int.TryParse(t, out var n) && n > 2
                  select t;                 // n is gone here
        Console.WriteLine(string.Join(",", big));
#if BAD
        var bad = from t in input
                  where int.TryParse(t, out var n)
                  select n;                 // another lambda
#endif
    }
}
