// 슬라이드 p12-v11-sh-cout — 제안서가 걱정한 쓰임, C# 11.0
using System;

// The proposal's own drawback: "implementing cout << "string" in C#"
sealed class Out
{
    public static readonly Out Cout = new Out();
    public static Out operator <<(Out o, string s)
    {
        Console.Write(s);
        return o;
    }
    public static Out operator <<(Out o, int n) => o << n.ToString();
}

class App
{
    static void Main()
    {
        Out cout = Out.Cout;
        cout = cout << "1 + 2 = " << (1 + 2) << "\n";
#if BAD
        string s = "x" << cout;            // first operand must be Out
#endif
    }
}
