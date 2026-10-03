// 슬라이드 p12-v11-raw-quotes — 내용보다 긴 구분자, C# 11.0
using System;

class App
{
    static void Main()
    {
        string a = """"He wrote """raw""" here."""";
        string b = """""" " "" """ """" """"" """""";
        Console.WriteLine(a);
        Console.WriteLine(b);
#if SAME
        string c = """
            five quotes: """""
            """;
#endif
    }
}
