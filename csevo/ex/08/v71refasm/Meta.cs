// 슬라이드 p8-v7_1-refasm — 어셈블리 특성의 형식 이름 읽기, C# 7.1
using System.Linq;
using System.Reflection.Metadata;

static class Meta
{
    // the name of each assembly-level attribute's type
    public static string[] AssemblyAttributes(MetadataReader md)
    {
        return md.GetAssemblyDefinition().GetCustomAttributes()
            .Select(h => TypeName(md, md.GetCustomAttribute(h)))
            .ToArray();
    }

    static string TypeName(MetadataReader md, CustomAttribute a)
    {
        EntityHandle c = a.Constructor;
        if (c.Kind == HandleKind.MethodDefinition)
        {
            var m = md.GetMethodDefinition((MethodDefinitionHandle)c);
            return md.GetString(md.GetTypeDefinition(
                m.GetDeclaringType()).Name);
        }
        EntityHandle p = md.GetMemberReference(
            (MemberReferenceHandle)c).Parent;
        return p.Kind != HandleKind.TypeReference ? "?" : md.GetString(
            md.GetTypeReference((TypeReferenceHandle)p).Name);
    }
}
