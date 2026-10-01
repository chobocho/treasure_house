// 슬라이드 p2-v1-usinglower — IDisposable 이 아니면, C# 1.0
using System.IO;
using System.Text;

class App
{
    static void Main()
    {
        using (StringBuilder sb = new StringBuilder())
        {
        }
        using (StringReader r = new StringReader("x"))
        {
            r = null;                    // the variable is read-only
        }
    }
}
