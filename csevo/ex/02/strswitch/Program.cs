// 슬라이드 p2-v1-strswitch — 문자열로 switch, C# 1.0
using System;

class App
{
    static string Run(string cmd)
    {
        switch (cmd)
        {
            case "start":
                return "starting";
            case "stop":
            case "halt":                      // stacked labels are fine
                return "stopping";
            case "restart":
                Console.Write("(stop) ");
                goto case "start";            // explicit jump
            default:
                return "unknown: " + (cmd == null ? "null" : cmd);
        }
    }

    static void Main()
    {
        Console.WriteLine(Run("start"));
        Console.WriteLine(Run("halt"));
        Console.WriteLine(Run("restart"));
        Console.WriteLine(Run("Start"));      // case-sensitive
        Console.WriteLine(Run(null));         // no exception
    }
}
