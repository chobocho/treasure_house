// 슬라이드 p7-v6-interp-culture — 보간은 현재 문화권을 따른다, C# 6.0
using System;
using System.Globalization;

class App
{
    static void Main()
    {
        double v = 1234.5;
        Console.WriteLine("current: [{0}]",
            CultureInfo.CurrentCulture.Name);
        Console.WriteLine($"{v:N1} {v}");

        CultureInfo.CurrentCulture = new CultureInfo("de-DE");
        Console.WriteLine($"{v:N1} {v}");          // follows de-DE

        // FormattableString lets the caller pick the culture
        FormattableString f = $"{v:N1} {v}";
        Console.WriteLine(FormattableString.Invariant(f));
        Console.WriteLine(f.ToString(CultureInfo.InvariantCulture));
    }
}
