// 슬라이드 p2-v1-finallyret — finally 를 떠날 수는 없다, C# 1.0
class App
{
    static int F()
    {
        try { return 1; }
        finally { return 2; }            // cannot leave a finally
    }

    static void G()
    {
        for (int i = 0; i < 3; i++)
        {
            try { }
            finally { break; }           // nor jump out of it
        }
    }

    static void Main() { }
}
