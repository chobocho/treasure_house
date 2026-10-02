// 슬라이드 p7-v6-nullcond-void — void 메서드와 ?., C# 6.0
using System;
using System.Text;

class App
{
    static void Main()
    {
        StringBuilder sb = null;
        sb?.Clear();                       // fine: a statement
        Action log = null;
        log?.Invoke();                     // fine
        sb = new StringBuilder("x");
        Console.WriteLine(sb?.Append("y")?.Append("z"));
#if BAD
        object r = log?.Invoke();          // void has no T?
#endif
    }
}
