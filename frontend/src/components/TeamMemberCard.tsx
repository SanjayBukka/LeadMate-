import React from 'react';
import { Mail, Code, Briefcase } from 'lucide-react';
import { TeamMember } from '../data/mockData';

interface TeamMemberCardProps {
  member: TeamMember;
}

type MemberExtras = {
  techStack?: string[];
  recentProjects?: string[];
};

export function TeamMemberCard({ member }: TeamMemberCardProps) {
  // Support additional optional fields if present in data
  const m = member as TeamMember & MemberExtras;

  // Provide sensible defaults based on role/name when explicit data isn't present
  const defaultStacksByRole: Record<string, string[]> = {
    'Frontend Developer': ['React', 'TypeScript', 'Tailwind CSS'],
    'Backend Developer': ['Node.js', 'Express', 'PostgreSQL'],
    'DevOps Engineer': ['Docker', 'Kubernetes', 'AWS'],
    'QA Engineer': ['Cypress', 'Jest', 'Playwright']
  };

  const defaultProjectsByName: Record<string, string[]> = {
    'Alice Cooper': ['E-Commerce Platform', 'CRM Dashboard'],
    'Bob Wilson': ['Mobile Banking App', 'API Gateway'],
    'Charlie Brown': ['CI/CD Pipeline', 'Monitoring Setup'],
    'David Smith': ['Automated Testing', 'Regression Suite']
  };

  const techStack = m.techStack ?? defaultStacksByRole[member.role] ?? ['JavaScript', 'Git'];
  const recentProjects = m.recentProjects ?? defaultProjectsByName[member.name] ?? ['Internal Tools'];

  return (
    <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 group">
      {/* Header with Avatar */}
      <div className="flex items-start space-x-4 mb-4">
        <div className="relative">
          <img
            src={member.avatar}
            alt={member.name}
            className="w-16 h-16 rounded-full object-cover ring-2 ring-blue-100 dark:ring-blue-900/30 group-hover:ring-blue-200 dark:group-hover:ring-blue-800 transition-all"
          />
          {/* Online Status */}
          <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full"></div>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg text-gray-900 dark:text-white truncate">
            {member.name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
            {member.role}
          </p>
          {m.experience && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {m.experience} experience
            </p>
          )}
        </div>
      </div>

      {/* Email */}
      <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-4 p-2 rounded-lg bg-gray-50 dark:bg-gray-700/50">
        <Mail className="w-4 h-4 flex-shrink-0" />
        <span className="truncate">{member.email}</span>
      </div>

      {/* Tech Stack */}
      <div className="mb-4">
        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400 mb-2">
          <Code className="w-4 h-4 mr-2 flex-shrink-0" />
          <span className="font-semibold text-gray-700 dark:text-gray-300">Tech Stack</span>
          <span className="ml-2 text-xs text-gray-400">({techStack.length})</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {techStack.slice(0, 6).map((tech) => (
            <span
              key={tech}
              className="px-2.5 py-1 text-xs font-medium rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 dark:from-blue-900/30 dark:to-purple-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800/50"
            >
              {tech}
            </span>
          ))}
          {techStack.length > 6 && (
            <span className="px-2.5 py-1 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
              +{techStack.length - 6} more
            </span>
          )}
        </div>
      </div>

      {/* Recent Projects */}
      <div>
        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400 mb-2">
          <Briefcase className="w-4 h-4 mr-2 flex-shrink-0" />
          <span className="font-semibold text-gray-700 dark:text-gray-300">Recent Projects</span>
        </div>
        {recentProjects.length > 0 ? (
          <ul className="space-y-1.5">
            {recentProjects.slice(0, 3).map((project) => (
              <li key={project} className="flex items-start space-x-2 text-sm text-gray-600 dark:text-gray-300">
                <span className="text-blue-500 dark:text-blue-400 mt-1">•</span>
                <span className="flex-1">{project}</span>
              </li>
            ))}
            {recentProjects.length > 3 && (
              <li className="text-xs text-gray-500 dark:text-gray-400 italic pl-4">
                +{recentProjects.length - 3} more projects
              </li>
            )}
          </ul>
        ) : (
          <p className="text-sm text-gray-400 dark:text-gray-500 italic">No projects listed</p>
        )}
      </div>
    </div>
  );
}