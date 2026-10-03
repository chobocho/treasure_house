// 슬라이드 p12-v11-raw-dedent — 닫는 따옴표가 정하는 들여쓰기, C# 11.0
using System;

class App
{
    static void Show(string s)
    {
        foreach (string line in s.Split('\n'))
            Console.WriteLine("|" + line);
        Console.WriteLine("---");
    }

    static void Main()
    {
        Show("""
            <a>
              <b/>
            </a>
            """);                     // closing quotes under '<'
        Show("""
            <a>
              <b/>
            </a>
          """);                       // two columns further left
        Show("""
            <a>
              <b/>
            </a>
""");                                 // column 1: nothing removed
    }
}
