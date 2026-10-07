// 슬라이드 p15-v14-dr-rules — #: 가 놓일 수 있는 자리, C# 14
#:property Nullable=enable
#if IFFIRST
#:property Foo=bar
#endif
using System;

class Program
{
    static void Main()
    {
        string code = """
            #:package NotADirective@1.0
            """;
        Console.WriteLine(code);
    }
}
#if AFTER
#:property TooLate=true
#endif
