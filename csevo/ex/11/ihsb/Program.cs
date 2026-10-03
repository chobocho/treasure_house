// 슬라이드 p11-v10-ih-sb — StringBuilder.Append 의 처리기, C# 10.0
using System;
using System.Text;

class App
{
    static void Row(string label, Action<StringBuilder, int> f)
    {
        var sb = new StringBuilder(1 << 16);
        f(sb, 1);                                    // warm up
        sb.Clear();
        long before = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 1000; i++) f(sb, i);
        long after = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"  {label,-28}{(after - before) / 1000,4}");
    }

    static void Main()
    {
        Console.WriteLine("bytes allocated per call:");
        Row("Append($\"n={i};\")",
            (sb, i) => sb.Append($"n={i};"));
        Row("Append(\"n=\" + i + \";\")",
            (sb, i) => sb.Append("n=" + i + ";"));
        Row("s = $\"n={i};\"; Append(s)",
            (sb, i) => { string s = $"n={i};"; sb.Append(s); });
        Row("AppendFormat(\"n={0};\", i)",
            (sb, i) => sb.AppendFormat("n={0};", i));
    }
}
