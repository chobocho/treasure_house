// 슬라이드 p2-v1-xmldoc — /// 문서 주석, C# 1.0
using System;
using System.IO;

/// <summary>Reads its own documentation file.</summary>
class App
{
    /// <summary>Adds <b>two numbers</summary>
    public static int Add(int a, int b) { return a + b; }

    /// <summary>Subtracts.</summary>
    /// <param name="x">first</param>
    /// <param name="c">no such parameter</param>
    public static int Sub(int x, int y) { return x - y; }

    static void Main()
    {
        if (!File.Exists("bin/doc.xml"))
        {
            Console.WriteLine("no doc file: build without -doc");
            return;
        }
        foreach (string line in File.ReadAllLines("bin/doc.xml"))
            if (line.IndexOf(":App") >= 0)
                Console.WriteLine(line.Trim());
    }
}
