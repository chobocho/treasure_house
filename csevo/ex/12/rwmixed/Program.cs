// 슬라이드 p12-v11-raw-mixed — 탭과 스페이스를 섞은 들여쓰기, C# 11.0
using System;

class App
{
    static void Main()
    {
        // every line below starts with TAB TAB SPACE SPACE;
        // the first content line has one more TAB after that
		  string s = """
		  	tab then text
		  same prefix
		  """;
        Console.WriteLine(s.Replace("\t", "<TAB>"));
    }
}
