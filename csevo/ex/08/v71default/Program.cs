// 슬라이드 p8-v7_1-default — default 리터럴, C# 7.1
using System;
using System.Linq;

class App
{
    static T FirstOr<T>(T[] items) =>
        items.Length > 0 ? items[0] : default;   // return position

    static string Describe(TimeSpan t) => t.TotalSeconds + "s";

    static void Main()
    {
        int n = default;                         // a local
        string s = default;
        Func<string, bool> where = default;      // from whats-new
        var words = new[] { default, "b" };      // array element
        Console.WriteLine(n + " " + (s == null) + " " +
            (where == null));
        Console.WriteLine(words.Count(w => w == null));
        Console.WriteLine(Describe(default));    // an argument
        Console.WriteLine(FirstOr(new int[0]));
        Console.WriteLine(FirstOr(new string[0]) == null);
        Console.WriteLine(default(DateTime).ToString("yyyy-MM-dd"));
    }
}
