// 슬라이드 p9-v8-switchexpr-stmt — 문과 식, C# 8.0
using System;

class App
{
    static string Statement(int code)
    {
        switch (code)
        {
            case 200:
                return "OK";
            case 404:
                return "Not Found";
            default:
                return "?";
        }
    }

    static string Expression(int code) => code switch
    {
        200 => "OK",
        404 => "Not Found",
        _ => "?",
    };

    static void Main()
    {
        foreach (int c in new[] { 200, 404, 500 })
            Console.WriteLine("{0} {1} | {2}",
                c, Statement(c), Expression(c));
#if BAD
        200 switch { 200 => "OK", _ => "?" };   // not a statement
#endif
    }
}
