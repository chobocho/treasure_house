// 슬라이드 p13-v12-al-scope — 별칭은 using 을 안 본다, C# 12.0
using System;
using System.Text;
using Pair = (int A, string B);           // keywords: always fine
using SB = System.Text.StringBuilder;     // full name: fine
#if SHORT
using SB2 = StringBuilder;                // 'using System.Text' ignored
#endif

class App
{
    static void Main()
    {
        var sb = new SB("x");
        Pair p = (1, "b");
        Console.WriteLine(sb.Append(p).ToString());
        Console.WriteLine(new StringBuilder("y"));
    }
}
