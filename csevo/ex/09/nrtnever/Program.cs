// 슬라이드 p9-v8-nrt-never — 언제나 null 이 아닌 식, C# 8.0
#nullable enable
using System;

class App
{
    string? name = null;

    string Describe(object? o)
    {
        string a = $"{o}";                  // interpolated string
        string b = nameof(name);            // nameof
        string c = typeof(App).Name;        // typeof
        object d = new object();            // new
        Func<int> e = () => 1;              // lambda
        string f = this.ToString()!;        // this, then !
        return a + b + c + d.GetType().Name + e() + f.Length;
    }

    static void Main()
    {
        Console.WriteLine(new App().Describe(null));
    }
}
