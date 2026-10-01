// 슬라이드 p2-v1-paramstrap — params object[] 의 함정, C# 1.0
using System;

class App
{
    static void Show(string label, params object[] args)
    {
        string n = args == null ? "null array" : args.Length + " args";
        Console.WriteLine(label.PadRight(24) + n);
    }

    static void Main()
    {
        Show("Show()");
        Show("Show(null)", null);
        Show("Show((object)null)", (object)null);
        Show("Show(1, \"x\")", 1, "x");
        Show("Show(string[2])", new string[] { "a", "b" });
        Show("Show(int[2])", new int[] { 1, 2 });
        Show("Show((object)string[2])", (object)new string[2]);
    }
}
