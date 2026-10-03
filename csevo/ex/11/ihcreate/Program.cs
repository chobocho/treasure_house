// 슬라이드 p11-v10-ih-create — string.Create 와 Span.TryWrite, C# 10.0
using System;
using System.Globalization;

class App
{
    static void Main()
    {
        var comma = (CultureInfo)CultureInfo.InvariantCulture.Clone();
        comma.NumberFormat.NumberDecimalSeparator = ",";
        double x = 1.5;

        Console.WriteLine($"{x}");                     // current
        Console.WriteLine(string.Create(comma, $"{x}")); // given

        Span<char> buf = stackalloc char[8];           // on the stack
        bool ok = buf.TryWrite($"x={x:F3}", out int n);
        Console.WriteLine($"{ok} {n} [{buf.Slice(0, n).ToString()}]");
        ok = buf.TryWrite($"x={x:F6}", out n);          // 10 chars > 8
        Console.WriteLine($"{ok} {n}");
        ok = buf.TryWrite(comma, $"{x:F2}", out n);
        Console.WriteLine($"{ok} {n} [{buf.Slice(0, n).ToString()}]");
    }
}
